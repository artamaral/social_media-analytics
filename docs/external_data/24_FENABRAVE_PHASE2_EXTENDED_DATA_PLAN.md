# Fase 2 - Expansao da ingestao Fenabrave

Data: 2026-07-06

## Objetivo

Expandir a ingestao mensal da Fenabrave para persistir dados que ja constam nos
PDFs preservados no Supabase Storage, mas ainda nao estao modelados no banco.

Esta fase deve manter o principio da fase 1:

- o PDF original continua sendo a fonte auditavel
- `market_source_files` continua sendo o registro do arquivo mensal
- cada dado persistido deve estar ligado ao `source_file_id`
- toda carga deve ter preview, validacao e status claro
- a implantacao deve ocorrer por item, sem tentar resolver todo o PDF de uma vez
- os PDFs ja existentes devem ser usados para popular o historico disponivel

## Contexto atual

A fase 1 esta documentada em
`docs/external_data/23_FENABRAVE_PHASE1_INGESTION_SPEC.md`.

Ela cobre:

- upload ou preservacao do PDF no bucket privado `market-source-files`
- registro do arquivo em `market_source_files`
- extracao da primeira tabela da pagina 1
- persistencia em `market_vehicle_registrations_segment`
- validacao estrutural dos segmentos
- consumo inicial por dashboard

A fase 2 nao substitui esse fluxo. Ela adiciona novas tabelas e validacoes para
rankings, marcas, modelos, eletrificados e canal de venda.

## Escopo dos novos dados

Fonte:

- Fenabrave

Arquivos:

- PDFs mensais ja carregados no Supabase Storage
- PDFs mensais futuros carregados pela rotina mensal do Streamlit

Granularidade:

- periodo mensal, sempre como `reference_period = primeiro dia do mes`
- Brasil como escopo inicial
- dado ligado a `source_file_id`

Persistencia:

- os novos dados devem ser mantidos no banco
- nao devem ficar apenas como preview transitivo
- cada item deve ter uma tabela normalizada ou uma tabela compartilhada com
  coluna de tipo de ranking, quando o formato permitir

## Lista de itens da fase 2

| Item | Dado | Pagina | Periodo publicado | Recorte | Persistir no banco |
|---:|---|---:|---|---|---|
| 1 | Ranking dos emplacamentos | 6 | mes | automoveis e comerciais leves | sim |
| 2 | Ranking dos emplacamentos | 6 | acumulado | automoveis e comerciais leves | sim |
| 3 | Ranking por marca | 8 | mes | automoveis e comerciais leves | sim |
| 4 | Ranking por marca | 9 | acumulado | automoveis e comerciais leves | sim |
| 5 | Emplacamentos por sub segmento | 17 | mes e acumulado | automoveis | sim |
| 6 | Mercado de eletrificados | 20 e 21 | mes | automoveis e comerciais leves | sim |
| 7 | Total por marca mes hibrido | 20 e 21 | mes | automoveis e comerciais leves hibridos | sim |
| 8 | Total por marca mes eletrico | 20 e 21 | mes | automoveis e comerciais leves eletricos | sim |
| 9 | Total por modelo leves hibrido | 20 | mes | leves hibridos | nao, fora do escopo ativo |
| 10 | Total por modelo leves eletrico | 20 | mes | leves eletricos | nao, fora do escopo ativo |
| 11 | Participacao de venda direta e varejo | 24 | mes | canal de venda | sim |
| 12 | Participacao de venda direta e varejo | 25 | acumulado | canal de venda | sim |
| 13 | Ranking por marca de emplacamento varejo | 26 | mes | varejo | sim |
| 14 | Ranking por marca de emplacamento varejo | 27 | acumulado | varejo | sim |
| 15 | Ranking por marca de emplacamento direta | 28 | mes | venda direta | sim |
| 16 | Ranking por marca de emplacamento direta | 29 | acumulado | venda direta | sim |
| 17 | Participacao de mercado consolidada por marca | 3 | mes | automoveis, comerciais leves e autos + comerciais leves | sim |
| 18 | Participacao de mercado consolidada por marca | 4 | acumulado | automoveis, comerciais leves e autos + comerciais leves | sim |
| 19 | Modelos mais emplacados venda direta | 30 | mes | venda direta | sim |
| 20 | Modelos mais emplacados venda varejo | 31 | mes | varejo | sim |
| 21 | Modelos mais emplacados venda direta | 32 | acumulado | venda direta | sim |
| 22 | Modelos mais emplacados venda varejo | 33 | acumulado | varejo | sim |

## Ordem de implantacao por item

A implantacao deve ser incremental. Cada item deve passar sozinho por desenho,
extracao, validacao, carga historica e liberacao.

Ordem recomendada:

| Fase | Itens | Motivo |
|---|---|---|
| 2.1 | 1 e 2 | ranking geral da pagina 6 e mais proximo da logica atual de mercado |
| 2.2 | 3 e 4 | ranking por marca de autos e comerciais leves |
| 2.3 | 11 e 12 | canal de venda direta/varejo, importante para separar comportamento de mercado |
| 2.4 | 13 a 16 | rankings por marca separados por canal |
| 2.5 | 17 e 18 | consolidado de participacao de mercado por marca nas paginas 3 e 4 |
| 2.6 | 19 a 22 | rankings por modelo separados por canal |
| 2.7 | 6 a 8 | eletrificados efetivamente publicados no bloco de mercado e marcas das paginas 20 e 21 |
| 2.8 | 5 | emplacamentos por subsegmento, com colunas de periodos `n` e `n-1` e cuidado adicional no contrato temporal |

A ordem pode mudar se a extracao de uma pagina se mostrar mais estavel que
outra, mas a regra continua: liberar um bloco somente depois de backfill,
validacao e aceite.

## Modelo de dados proposto

### 1. Controle de itens extraidos

Criar uma tabela de controle para registrar o estado de cada item do PDF por
arquivo.

Nome proposto:

```text
market_fenabrave_extraction_items
```

Campos conceituais:

```text
id
source_file_id
reference_period
item_code
item_label
pdf_page
published_period_type        -- monthly ou accumulated
market_scope                 -- Brasil inicialmente
status                       -- pending, extracted, validated, failed, skipped
row_count
validation_status            -- passed, warning, failed
validation_notes
created_at
updated_at
```

Uso:

- saber quais itens de cada PDF ja foram processados
- identificar dados que existem no PDF, mas ainda faltam no banco
- permitir backfill parcial por item
- evitar que uma falha em uma pagina bloqueie as demais

### 2. Rankings gerais de emplacamento

Itens cobertos:

- 1
- 2

Nome proposto:

```text
market_vehicle_registration_rankings
```

Campos conceituais:

```text
id
source_file_id
reference_period
item_code
published_period_type        -- monthly ou accumulated
rank_position
brand_name
model_name
vehicle_category             -- autos_comerciais_leves
units
market_share_pct
raw_label
created_at
```

Chave unica sugerida:

```text
source_file_id, item_code, published_period_type, rank_position, brand_name, model_name
```

### 3. Rankings por marca

Itens cobertos:

- 3
- 4
- 13
- 14
- 15
- 16

Nome proposto:

```text
market_vehicle_brand_rankings
```

Campos conceituais:

```text
id
source_file_id
reference_period
item_code
published_period_type        -- monthly ou accumulated
sales_channel                -- all, retail, direct
vehicle_category             -- autos_comerciais_leves
rank_position
brand_name
units                        -- nullable para itens publicados apenas com share
market_share_pct
raw_label
created_at
```

Chave unica sugerida:

```text
source_file_id, item_code, published_period_type, sales_channel, rank_position, brand_name
```

Decisao de modelagem aplicada em 2026-07-12:

- `market_vehicle_brand_rankings` passa a suportar dois contratos no mesmo
  schema:
  - rankings com `units` e `market_share_pct`, como os itens `3` e `4`
  - rankings apenas com `market_share_pct`, como os itens `13` a `16`
- para isso, `units` deixa de ser obrigatorio na tabela, mas a modelagem passa
  a exigir que pelo menos um entre `units` e `market_share_pct` esteja
  preenchido
- essa decisao preserva reuso da tabela por item e evita criar uma tabela
  paralela apenas para o breakdown por canal

### 4. Rankings por modelo

Itens cobertos:

- 5
- 17
- 18
- 19
- 20

Nome proposto:

```text
market_vehicle_model_rankings
```

Campos conceituais:

```text
id
source_file_id
reference_period
item_code
published_period_type        -- monthly ou accumulated
sales_channel                -- all, retail, direct
vehicle_category             -- autos
subsegment_name
rank_position
brand_name
model_name
units
market_share_pct
raw_label
created_at
```

Chave unica sugerida:

```text
source_file_id, item_code, published_period_type, sales_channel, subsegment_name, rank_position, brand_name, model_name
```

### 5. Eletrificados

Itens cobertos:

- 6
- 7
- 8

Nome proposto:

```text
market_vehicle_electrified_registrations
```

Campos conceituais:

```text
id
source_file_id
reference_period
item_code
published_period_type        -- monthly nesta fase
aggregation_level            -- market, brand, model
powertrain_type              -- electric, hybrid
vehicle_category             -- automoveis ou comerciais_leves
rank_position
brand_name
model_name
units
market_share_pct
raw_label
created_at
```

Chave unica sugerida:

```text
source_file_id, item_code, aggregation_level, powertrain_type, rank_position, brand_name, model_name
```

Observacao operacional refinada para os itens `6`, `7` e `8`:

- a pagina `20` cobre `automoveis`
- a pagina `21` cobre `comerciais_leves`
- as duas paginas seguem o mesmo desenho com `3` blocos relevantes
- o bloco `1` traz `A) Hibridos`, `B) Eletricos` e `Tot.Eletrificados`
- no bloco `1`, o escopo inicial deve persistir apenas a `coluna 1`, isto e,
  o valor absoluto do mes
- as demais colunas do bloco `1` representam outros meses, acumulados ou
  comparativos e ficam fora do escopo inicial de persistencia
- o bloco `2` traz `Hibridos mes`, por marca, com `fabricante` e `quantidade`
- o bloco `3` traz `Eletricos mes`, por marca, com `fabricante` e `quantidade`
- a implementacao deve manter `item_code` separado para `6`, `7` e `8`, mas
  pode usar um parser compartilhado para as paginas `20` e `21`
- no item `6`, o campo `powertrain_type` precisa suportar tambem a linha
  consolidada `total_electrified`, alem de `hybrid` e `electric`

Decisao de escopo para os itens `9` e `10`:

- a revisao operacional da pagina `20` confirmou que o bloco efetivamente
  publicado pela Fenabrave cobre mercado consolidado e rankings por `marca`,
  nao rankings por `modelo`
- por isso, os itens `9` e `10` nao representam um dado realmente disponivel
  no PDF atual e devem ser tratados como desejo analitico, nao como backlog
  tecnico de extracao da fase 2
- esses itens saem do escopo ativo da fase 2 enquanto nao houver evidencia de
  publicacao explicita por modelo em PDFs futuros

### 6. Participacao por canal de venda

Itens cobertos:

- 11
- 12

Decisao tecnica registrada:

- apesar de as paginas `24` e `25` serem apresentadas como graficos no PDF, a
  Fenabrave publica os percentuais de `Venda Direta` e `Varejo` como texto
  extraivel em regioes estaveis da pagina
- a implementacao deve usar parser por regioes fixas, com recorte por bloco de
  categoria (`automoveis`, `comerciais_leves`, `autos_comerciais_leves`),
  evitando OCR
- a validacao precisa confirmar sempre `2` canais por categoria e soma
  aproximada de `100%`, aceitando pequena variacao por arredondamento grafico
- o parser deve tratar tanto percentual com virgula quanto percentual com ponto,
  pois os artefatos de extracao podem variar conforme a camada de texto do PDF

Nome proposto:

```text
market_vehicle_sales_channel_mix
```

Campos conceituais:

```text
id
source_file_id
reference_period
item_code
published_period_type        -- monthly ou accumulated
sales_channel                -- retail ou direct
vehicle_category             -- autos_comerciais_leves ou total publicado
share_pct
raw_label
created_at
```

Chave unica sugerida:

```text
source_file_id, item_code, published_period_type, sales_channel, vehicle_category
```

### 7. Participacao de mercado consolidada por marca

Itens cobertos:

- 17
- 18

Decisao tecnica registrada:

- as paginas `3` e `4` passam a fazer parte do escopo ativo porque funcionam
  como consolidado total do bloco de participacao de mercado cujo breakdown por
  canal esta nas paginas `26` a `29`
- o parser deve ser posicional, por regioes fixas, da mesma forma adotada para
  os graficos de canal de venda das paginas `24` e `25`
- este bloco nao substitui os itens `3` e `4`, porque aqui o foco publicado e
  `participacao por marca` em graficos percentuais e com terceira visao
  `autos + comerciais leves`
- os itens `17` e `18` devem preservar separadamente as tres categorias
  publicadas: `automoveis`, `comerciais_leves` e
  `autos_comerciais_leves`

Nome proposto:

```text
market_vehicle_brand_market_share
```

Campos conceituais:

```text
id
source_file_id
reference_period
item_code
published_period_type        -- monthly ou accumulated
market_scope
vehicle_category             -- automoveis, comerciais_leves, autos_comerciais_leves
rank_position
brand_name_raw
share_pct
raw_label
created_at
```

Chave unica sugerida:

```text
source_file_id, item_code, published_period_type, vehicle_category, rank_position
```

Referencia de implementacao:

- ver plano tecnico detalhado em
  `docs/external_data/26_FENABRAVE_PHASE2_ITEMS13_18_TECHNICAL_PLAN.md`

## Processo mensal atualizado

O processo mensal deve continuar com o mesmo inicio da fase 1:

```text
1. Confirmar publicacao oficial da Fenabrave
2. Carregar PDF no bucket privado market-source-files
3. Registrar ou atualizar market_source_files
4. Gerar preview da tabela de segmentos
5. Gravar market_vehicle_registrations_segment
6. Validar segmentos e liberar o periodo base
```

Depois da liberacao base, executar a fase 2 por item:

```text
7. Listar itens esperados para o PDF do periodo
8. Para cada item, extrair apenas a pagina/bloco correspondente
9. Gerar preview do item
10. Validar contagem, totais, ranking e consistencia contra o PDF
11. Gravar a tabela normalizada do item
12. Registrar status do item em market_fenabrave_extraction_items
13. Repetir ate concluir todos os itens habilitados
14. Liberar views de consumo somente para itens validated ou warning aceito
```

Regra operacional:

- um item com falha nao deve apagar nem bloquear itens ja validados
- reprocessamento deve ser feito por `source_file_id` e `item_code`
- `--replace` deve substituir somente o item em reprocessamento
- a rotina mensal deve mostrar claramente quais itens estao pendentes

Contrato de automacao mensal:

- todo item da fase 2 que for implementado deixa de ser uma extracao avulsa e
  passa a fazer parte da inclusao mensal padrao da Fenabrave
- apos o upload/registro do PDF mensal e a validacao da fase 1, a rotina deve
  executar automaticamente todos os itens da fase 2 marcados como ativos
- cada item ativo deve gravar seus dados no banco, atualizar
  `market_fenabrave_extraction_items` e expor status de sucesso, warning ou
  falha para o periodo
- falhas em itens ativos devem aparecer como pendencia operacional do mes, nao
  como ausencia silenciosa de dados
- a automacao mensal deve permitir reprocessamento por item e por periodo, sem
  duplicar linhas e sem apagar dados de outros itens
- itens ainda nao implementados ficam como backlog ou `pending`, mas nao devem
  impedir a carga mensal dos itens ja ativos

## Metodo para validar PDFs ja carregados, mas ainda nao persistidos

Criar uma auditoria de cobertura por periodo e por item.

Entrada:

- todos os registros Fenabrave em `market_source_files`
- lista de itens esperados da fase 2
- registros ja gravados nas novas tabelas
- status de `market_fenabrave_extraction_items`

Saida esperada:

```text
reference_period
source_file_id
storage_path
item_code
item_label
expected_pdf_page
expected_table
db_table
db_row_count
item_status
coverage_status
notes
```

Estados de cobertura:

| Status | Significado |
|---|---|
| `missing_from_db` | o PDF existe, mas o item ainda nao foi gravado |
| `extracted_not_validated` | ha linhas no banco, mas o item ainda nao passou nos checks |
| `validated` | item carregado e validado |
| `warning_accepted` | item carregado com warning aceito |
| `failed` | tentativa registrada com erro |
| `not_applicable` | item nao existe nesse layout/periodo do PDF |

Checks minimos da auditoria:

- todo PDF validado na fase 1 deve ter os 20 itens com status conhecido
- nenhum item habilitado deve ficar invisivel, isto e, sem linha de controle
- todo item `validated` deve ter `db_row_count > 0`
- todo item com linhas no banco deve ter `source_file_id` existente em
  `market_source_files`
- nenhum item deve misturar dados de meses diferentes no mesmo `source_file_id`

## Backfill dos PDFs existentes

O backfill deve carregar todos os meses que ja possuem PDF no Storage e registro
em `market_source_files`.

Ordem recomendada:

```text
1. Inventariar PDFs Fenabrave existentes
2. Confirmar reference_period, storage_path, sha256 e extraction_status
3. Criar matriz periodo x item
4. Marcar todos os itens ainda nao processados como pending
5. Executar backfill do item 1 para todos os PDFs
6. Validar item 1 em todos os periodos
7. Executar backfill do item 2 para todos os PDFs
8. Validar item 2 em todos os periodos
9. Repetir ate o item 22
10. Gerar relatorio final de cobertura
```

Regra importante:

- a populacao historica deve ser por item em todos os meses, nao por mes em
  todos os itens

Motivo:

- fica mais facil estabilizar um parser por pagina/bloco
- erros de layout ficam concentrados no item correspondente
- a validacao comparativa entre meses fica mais simples
- evita liberar dados mistos com alguns itens maduros e outros ainda incertos

## Validacoes por tipo de dado

### Validacoes comuns

Aplicar a todos os itens:

- `source_file_id` obrigatorio e existente
- `reference_period` igual ao periodo do arquivo
- `item_code` obrigatorio
- `published_period_type` coerente com a pagina
- `rank_position` numerico quando houver ranking
- `units` inteiro nao negativo quando houver volume
- percentuais entre 0 e 100 quando houver participacao
- nomes de marca e modelo sem vazio quando forem chave do ranking
- nao permitir duplicidade pela chave unica do item
- `row_count` do controle deve bater com a tabela normalizada

### Validacoes de ranking

Aplicar aos itens 1, 2, 3, 4, 13, 14, 15, 16, 17, 18, 19, 20, 21 e 22:

- ranking deve iniciar em 1
- ranking nao deve ter posicoes duplicadas dentro do item
- unidades devem ser decrescentes ou empatar sem quebrar a ordem visual
- top N extraido deve bater com a quantidade de linhas esperada da pagina
- total das linhas do ranking nao deve exceder o total do segmento/canal
  correspondente quando houver base comparavel

Nota operacional refinada em 2026-07-12 para os itens `19` e `20`:

- o breakdown por canal das paginas `30` e `31` segue o mesmo contrato de
  ranking por modelo do bloco geral, mas o `top N` publicado pode variar por
  categoria dentro da propria pagina
- no piloto de `06/2026`, a pagina `30` publicou `50` linhas para
  `automoveis` e `41` para `comerciais_leves` em `venda direta`
- por isso, a validacao desses itens deve exigir ranks continuos de `1` ate a
  ultima linha publicada em cada categoria, sem assumir `50` linhas fixas como
  regra universal do breakdown por canal

### Validacoes de mensal versus acumulado

Aplicar aos pares:

- item 1 contra item 2
- item 3 contra item 4
- item 11 contra item 12
- item 13 contra item 14
- item 15 contra item 16
- item 17 contra item 18
- item 19 contra item 21
- item 20 contra item 22

Checks:

- acumulado do ano deve ser maior ou igual ao valor mensal do mesmo periodo
- acumulado de um mes deve ser maior ou igual ao acumulado do mes anterior
  dentro do mesmo ano, quando o item existir nos dois meses
- em janeiro, acumulado deve ser igual ou muito proximo do mensal, salvo regra
  especifica do PDF
- acumulado publicado deve ser tratado como dado publicado, nao recalculado
  silenciosamente pela soma mensal sem comparacao

### Validacoes de canal de venda

Aplicar aos itens 11 a 22:

- `retail + direct` deve bater com o total comparavel quando o PDF trouxer a
  base
- participacoes de varejo e direta devem somar 100% ou fechar dentro da margem
  de arredondamento definida
- rankings de varejo e direta devem ter `sales_channel` preenchido corretamente
- itens mensais e acumulados nao devem ser misturados

### Validacoes de eletrificados

Aplicar aos itens 6 a 8:

- `powertrain_type` deve ser `hybrid`, `electric` ou `total_electrified`
  quando o item for o bloco de mercado consolidado
- itens de marca nao devem gravar `model_name`
- itens de modelo devem gravar `brand_name` e `model_name`, quando o PDF
  permitir identificar ambos
- totais por marca/modelo nao devem exceder o total de eletrificados do mesmo
  tipo de propulsao, salvo se o PDF usar recorte diferente documentado
- eletricos e hibridos devem ser carregados como categorias separadas
- no item `6`, `hybrid + electric` deve bater com `total_electrified` dentro da
  margem de arredondamento ou de eventual diferenca publicada no proprio PDF
- no item `6`, somente a primeira coluna de volume mensal entra na
  persistencia inicial; colunas de mes anterior, acumulado e comparativos ficam
  apenas para auditoria futura
- os itens `7` e `8` devem usar apenas os blocos mensais por marca, ignorando
  os blocos acumulados enquanto eles nao fizerem parte do escopo ativo

### Validacoes de subsegmento

Aplicar ao item 5:

- `subsegment_name` obrigatorio
- cada linha deve representar um subsegmento valido de automoveis
- o nome persistido do subsegmento deve remover o prefixo tecnico `AU -`
- a coluna de mes anterior pode ser lida para auditoria, mas nao deve ser
  persistida como dado principal do item
- o parser deve persistir o mes corrente do periodo, o acumulado do ano
  corrente (`n`) e o acumulado do ano anterior (`n-1`)
- dezembro/2025 deve manter o acumulado de `2024` como `n-1`, sem colapsar esse
  valor no mesmo campo do acumulado de `2025`
- os acumulados precisam distinguir explicitamente o ano de referencia do
  acumulado publicado, porque a tabela sempre traz comparacao entre `n` e `n-1`
- paginas `16`, `18` e `19` devem ficar fora da analise principal do item `5`,
  pois funcionam apenas como breakdown complementar do bloco principal da
  pagina `17`

### Observacao operacional do item 5

Confirmacao manual com os PDFs carregados:

- o titulo conceitual correto do item `5` deve ser tratado como
  `Emplacamentos por sub segmento`
- a pagina principal do item e a `17`
- a tabela relevante traz, por linha de subsegmento:
  `mes corrente`, `mes anterior`, `acumulado n-1` e `acumulado n`
- o nome da subcategoria deve ser normalizado sem o prefixo `AU -`
- os valores publicados nesse bloco aparecem como percentuais por subsegmento,
  e nao como totais absolutos por modelo
- a coluna de `mes anterior` nao entra no escopo inicial de persistencia
- os campos de acumulado precisam suportar comparacao interanual publicada no
  proprio PDF, inclusive quando o periodo corrente for `12/2025` e o
  acumulado anterior for `2024`
- a pagina `16` mostra apenas um breakdown especifico de `Suv's` e nao deve ser
  tratada como a tabela principal do item `5`

## Views de consumo esperadas

As views devem ser criadas somente depois das tabelas e validacoes de cada bloco.

Views propostas:

```text
v_market_fenabrave_brand_rankings
v_market_fenabrave_model_rankings
v_market_fenabrave_sales_channel_mix
v_market_fenabrave_electrified_registrations
v_market_fenabrave_extraction_coverage
```

Regras:

- as views devem expor apenas dados `validated` ou `warning_accepted`
- cada linha deve manter `source_name`, `source_url`, `storage_path` e
  `captured_at`
- o dashboard deve consumir views, nao tabelas brutas
- perguntas via ChatGPT/API devem receber periodo, fonte e limite conhecido

## Criterios de aceite por item

Um item so pode ser considerado concluido quando:

- a estrutura de destino estiver documentada
- o parser do item gerar preview legivel
- pelo menos um PDF piloto estiver validado visualmente
- todos os PDFs ja carregados aplicaveis tiverem status conhecido
- os meses aplicaveis estiverem carregados ou marcados como excecao
- as validacoes automaticas passarem ou tiverem warning aceito
- a view de cobertura nao mostrar `missing_from_db` para esse item
- o item puder ser reprocessado sem duplicar linhas

## Fora do escopo deste plano

- implementar o parser
- criar migrations SQL
- alterar o Streamlit
- carregar dados reais
- automatizar download direto do site da Fenabrave
- normalizar taxonomia canonica completa de marcas e modelos
- cruzar Fenabrave com YouTube ou catalogo tecnico

## Riscos e cuidados

| Risco | Mitigacao |
|---|---|
| Layout do PDF muda entre meses | manter controle por item e status por periodo |
| Tabelas extraidas com colunas deslocadas | exigir preview e validacao visual no piloto |
| Marca/modelo com nomes inconsistentes | guardar `raw_label` e normalizar em camada posterior |
| Acumulado publicado diverge da soma mensal | persistir o acumulado publicado e registrar comparacao em validacao |
| Backfill parcial parecer completo | usar view de cobertura periodo x item |
| Dados misturados entre meses | validar `reference_period` contra storage path e nome original |
| Reprocessamento duplicar linhas | exigir chaves unicas por item e modo replace por item |

## Nota operacional

### Dezembro de 2025

Na execucao real do item 1, foi identificado que dezembro/2025 possuia
inconsistencia historica em `market_source_files`:

- dois registros para o mesmo PDF oficial, `id = 8` e `id = 17`
- `id = 17` como registro mensal canonico com `reference_period = 2025-12-01`
- `id = 8` como registro legado duplicado com `reference_period = 2025-12-02`
- ambos apontavam para `storage_path` incorreto
  `fenabrave/2025/12/2026_05_02.pdf`

Correcao aplicada:

- os dados analiticos foram preservados
- o item 1 foi gravado no registro canonico `id = 17`
- os dois registros tiveram metadados corrigidos para o objeto real
  `fenabrave/2025/12/2025_12_02.pdf`
- o registro `id = 8` foi mantido apenas por rastreabilidade, com nota de
  legado duplicado

Diretriz:

- ao executar backfill historico, tratar `id = 17` como referencia oficial de
  dezembro/2025
- nao apagar automaticamente registros legados sem antes confirmar impactos em
  tabelas dependentes

Atualizacao operacional de 2026-07-12:

- a duplicidade residual de `12/2025` em
  `market_vehicle_registrations_segment`, causada pela carga antiga no
  `source_file_id = 8`, foi removida do banco
- a tabela de segmentos do periodo voltou a manter apenas o conjunto canonico
  ligado ao `source_file_id = 17`
- o registro `id = 8` foi mantido temporariamente em `market_source_files`
  apenas como duplicidade historica rastreavel, sem permanecer como fonte
  valida de linhas analiticas
- em 2026-07-12 a duplicidade cadastral tambem foi saneada em
  `market_source_files`, com remocao do `id = 8` depois de confirmar ausencia
  de dependencias nas tabelas analiticas e de auditoria; a referencia canonica
  de `12/2025` passa a ser apenas o `source_file_id = 17`

## Status atual

### Item 1 concluido no historico disponivel

Status consolidado em 2026-07-07:

- item 1 implementado na rotina mensal automatica da Fenabrave
- preview operacional disponivel no Streamlit para revisao antes da gravacao
- persistencia habilitada em `market_vehicle_model_rankings`
- controle operacional habilitado em `market_fenabrave_extraction_items`
- views de consumo do item 1 ja criadas

Backfill historico executado e validado para os PDFs atualmente disponiveis:

| Periodo | source_file_id | Situacao do item 1 | Linhas gravadas |
|---|---:|---|---:|
| 12/2025 | 17 | validated / passed | 100 |
| 01/2026 | 5 | validated / passed | 100 |
| 02/2026 | 4 | validated / passed | 100 |
| 03/2026 | 3 | validated / passed | 100 |
| 04/2026 | 2 | validated / passed | 100 |
| 05/2026 | 6 | validated / passed | 100 |
| 06/2026 | 13 | validated / passed | 100 |

Observacoes operacionais:

- o backfill foi executado por item, mes a mes, conforme a estrategia definida
  neste plano
- todos os periodos acima ficaram com `validation_status = passed`
- todos os periodos acima ficaram com `row_count = 100` no controle do item
- a extracao de segmentos continua emitindo apenas o warning conhecido de
  ausencia da linha `total` no PDF extraido, sem bloquear a carga
- o registro legado `source_file_id = 8` permaneceu fora da carga analitica e
  deve continuar sendo tratado apenas como duplicidade historica rastreavel

Atualizacao consolidada de 2026-07-08:

- os itens `2`, `3` e `4` foram concluidos seguindo o mesmo padrao incremental do
  item `1`: parser, preview operacional no Streamlit, validacoes locais,
  persistencia no banco e backfill historico por PDF existente
- o item `4` (`Ranking por marca acumulado`, pagina `9`) passou a gravar em
  `market_vehicle_brand_rankings` com `published_period_type = accumulated`,
  `sales_channel = all` e `21` linhas por categoria
- o backfill oficial do item `4` foi concluido para `12/2025` a `06/2026`,
  usando os `source_file_id` canônicos `17`, `5`, `4`, `3`, `2`, `6` e `13`
- todos os periodos do item `4` ficaram com `status = validated`,
  `validation_status = passed` e `row_count = 42`
- o registro legado `source_file_id = 8` continua fora da carga analitica e deve
  permanecer apenas como duplicidade historica rastreavel

Pendencias para a fase 2 a partir deste ponto:

- iniciar o item `5` com o mesmo padrao de parser, preview, validacao e
  backfill, usando a pagina `17` do PDF
- manter a documentacao e a auditoria de cobertura atualizadas a cada novo item
  liberado

Atualizacao consolidada de 2026-07-09:

- o item `5` foi concluido e saiu da fila ativa, com parser, preview,
  persistencia e backfill historico ja documentados no backlog e nos artefatos
  da fase 2
- os itens `6`, `7` e `8` entraram em implementacao conjunta porque compartilham
  as paginas `20` e `21` e a mesma familia de validacoes operacionais
- o contrato funcional dos itens `6`, `7` e `8` foi refinado e documentado:
  `item 6` persiste apenas a primeira coluna mensal do bloco consolidado de
  mercado, enquanto `itens 7 e 8` persistem os blocos mensais por marca para
  `hibridos` e `eletricos`
- o parser base e o preview operacional no Streamlit ja foram implementados
  para os itens `6`, `7` e `8`
- no piloto com `06/2026`, o `item 6` extraiu corretamente os dados de
  `automoveis` e `comerciais_leves`, incluindo a reconciliacao esperada entre
  `hybrid`, `electric` e `total_electrified`
- no mesmo piloto, os `itens 7 e 8` extraem corretamente os rankings de marca
  para `automoveis`
- a principal pendencia tecnica atual ficou concentrada na pagina `21`, onde os
  blocos de `comerciais_leves` de `Hibridos mes` e `Eletricos mes` variam em
  posicao vertical e nao sao capturados com seguranca pelo fluxo textual simples
- foi feita uma validacao historica de layout dos PDFs de `12/2025` a `06/2026`
  e a conclusao operacional e que a abordagem correta para a pagina `21` deve
  ser por `regioes posicionadas`, com `x` fixo por bloco e `y` tolerante
  conforme a altura efetiva das tabelas
- a persistencia no banco para os itens `6`, `7` e `8` ainda nao foi ativada;
  nesta etapa a entrega habilitada e de parser, preview e validacoes iniciais

Pendencias imediatas a partir deste ponto:

- ajustar a extracao da pagina `21` com leitura por regiao para capturar
  corretamente os blocos mensais de `comerciais_leves`
- reexecutar o piloto de `06/2026` para confirmar `item 7` e `item 8` completos
  nas duas categorias
- somente depois disso ativar persistencia, controle em
  `market_fenabrave_extraction_items` e backfill historico dos itens `6`, `7` e
  `8`

Atualizacao complementar de 2026-07-09:

- a extracao da pagina `21` foi ajustada com leitura por `regiao posicionada`
  para os blocos mensais de `comerciais_leves`
- o recorte posicional passou a isolar corretamente `Hibridos mes` e
  `Eletricos mes` mesmo quando a altura vertical do bloco varia entre meses
- a validacao historica local de `12/2025` a `06/2026` passou sem falhas de
  severidade `error` para os itens `7` e `8`
- as quantidades de linhas por mes variam conforme o PDF publicado, mas agora
  aparecem de forma consistente em `comerciais_leves`:
  `item 7` entre `3` e `4` marcas e `item 8` entre `3` e `9` marcas no
  historico testado
- com isso, o parser e o preview dos itens `6`, `7` e `8` ficam estabilizados
  para o historico atualmente disponivel

Proximo passo operacional dos itens `6`, `7` e `8`:

- habilitar persistencia em
  `market_vehicle_electrified_registrations`
- registrar o status por item em
  `market_fenabrave_extraction_items`
- executar o backfill historico de `12/2025` a `06/2026`

Atualizacao final de 2026-07-09 para os itens `6`, `7` e `8`:

- a tabela `public.market_vehicle_electrified_registrations` foi criada no
  Supabase e passou a receber os dados dos itens `6`, `7` e `8`
- a rotina mensal Fenabrave foi atualizada para persistir esses itens no mesmo
  fluxo operacional dos itens anteriores, com suporte a `--replace`
- o Streamlit passou a enviar os itens `6`, `7` e `8` na acao de gravacao
  analitica do preview operacional
- o piloto de `06/2026` foi executado com sucesso no banco real
- o backfill historico oficial foi concluido para os `source_file_id`
  canonicos `17`, `5`, `4`, `3`, `2`, `6` e `13`, cobrindo `12/2025` a
  `06/2026`
- todos os periodos carregados ficaram com `status = validated`,
  `validation_status = passed` e com contagem de linhas coerente por item:
  `item 6` com `6` linhas em todos os meses, `item 7` entre `18` e `19`
  linhas, e `item 8` entre `18` e `24` linhas
- o `source_file_id = 8` continua fora da carga analitica e deve permanecer
  apenas como duplicidade historica rastreavel de `12/2025`

Estado consolidado apos o backfill:

- itens `6`, `7` e `8` concluídos no historico atualmente disponivel
- parser, preview, persistencia, controle por item e backfill historico todos
  validados no banco
- itens `11` e `12` confirmados como viaveis sem OCR, usando extracao textual
  por regiao fixa nas paginas `24` e `25`; a proxima etapa operacional e ligar
  a persistencia em `market_vehicle_sales_channel_mix` e executar o backfill
- foi confirmada a retirada dos itens `9` e `10` do escopo ativo, porque a
  pagina `20` nao publica o dado por modelo; esse ponto passa a ser tratado
  como desejo analitico, nao como dado disponivel
- com isso, a proxima frente real da fase 2 avanca para os itens `11` e `12`,
  referentes a participacao de venda direta e varejo nas paginas `24` e `25`

Atualizacao consolidada de 2026-07-12:

- os itens `13` e `14` foram concluidos no mesmo contrato incremental da fase
  2: parser posicional, preview operacional no Streamlit, validacoes locais,
  persistencia no banco e backfill historico por PDF existente
- `market_vehicle_brand_rankings` passou a aceitar dois contratos na mesma
  tabela: rankings por marca com `units + market_share_pct` e rankings por
  participacao com `units = null` e `market_share_pct` preenchido
- o mesmo ajuste de modelagem passou a aceitar explicitamente a categoria
  `autos_comerciais_leves`, necessaria para os blocos combinados das paginas
  `26` a `29`
- o backfill oficial dos itens `13` e `14` foi concluido para `12/2025` a
  `06/2026`, usando os `source_file_id` canonicos `17`, `5`, `4`, `3`, `2`,
  `6` e `13`
- todos os periodos carregados ficaram com `status = validated`,
  `validation_status = passed` e `row_count = 30` em
  `market_fenabrave_extraction_items`
- no banco final, cada periodo passou a ter `10` linhas por categoria
  (`automoveis`, `comerciais_leves` e `autos_comerciais_leves`) para o item
  `13` e para o item `14`
- a proxima frente prioritaria da fase 2 passa a ser o item `15`,
  `Ranking por marca de emplacamento direta`, pagina `28`, reaproveitando o
  mesmo parser posicional e a mesma modelagem de share por marca

Atualizacao complementar de 2026-07-12:

- o item `15` foi concluido no historico atualmente disponivel seguindo o
  mesmo contrato dos itens `13` e `14`: parser posicional, preview
  operacional no Streamlit, validacoes locais, persistencia no banco e
  backfill historico por PDF existente
- a correcao canonica de marca `ITSUBISHI -> MITSUBISHI` ficou incorporada ao
  parser de share por marca, preservando o texto bruto para auditoria local
- o backfill oficial do item `15` foi concluido para `12/2025` a `06/2026`,
  usando os `source_file_id` canonicos `17`, `5`, `4`, `3`, `2`, `6` e `13`
- todos os periodos carregados ficaram com `status = validated`,
  `validation_status = passed` e `row_count = 30` em
  `market_fenabrave_extraction_items`
- no banco final, cada periodo passou a ter `10` linhas por categoria
  (`automoveis`, `comerciais_leves` e `autos_comerciais_leves`) para o item
  `15`
- com isso, a proxima frente prioritaria da fase 2 passa a ser o item `16`,
  `Ranking por marca de emplacamento direta acumulado`, pagina `29`

Atualizacao complementar de 2026-07-12 para os itens 16, 17 e 18:

- o item `16` foi concluido no historico atualmente disponivel seguindo o
  mesmo contrato do item `15`: parser posicional, preview operacional no
  Streamlit, validacoes locais, persistencia no banco e backfill historico por
  PDF existente
- o backfill oficial do item `16` foi concluido para `12/2025` a `06/2026`,
  usando os `source_file_id` canonicos `17`, `5`, `4`, `3`, `2`, `6` e `13`
- todos os periodos carregados do item `16` ficaram com
  `status = validated`, `validation_status = passed` e `row_count = 30` em
  `market_fenabrave_extraction_items`
- no banco final, cada periodo do item `16` passou a ter `10` linhas por
  categoria (`automoveis`, `comerciais_leves` e
  `autos_comerciais_leves`)
- os itens `17` e `18`, referentes ao consolidado de participacao de mercado
  por marca nas paginas `3` e `4`, passaram a reutilizar a mesma tabela
  `market_vehicle_brand_rankings`
- para esse consolidado, o contrato adotado e `sales_channel = all`,
  `units = null` e `market_share_pct` como medida principal
- o piloto local de `06/2026` confirmou que as paginas `3` e `4` respondem ao
  mesmo parser posicional ja estabilizado nas paginas `26` a `29`
- o piloto de `06/2026` foi executado com sucesso no banco real e liberou o
  backfill historico oficial dos itens `17` e `18`
- o backfill oficial dos itens `17` e `18` foi concluido para `12/2025` a
  `06/2026`, usando os `source_file_id` canonicos `17`, `5`, `4`, `3`, `2`,
  `6` e `13`
- todos os periodos carregados dos itens `17` e `18` ficaram com
  `status = validated`, `validation_status = passed` e `row_count = 33` em
  `market_fenabrave_extraction_items`
- no banco final, cada periodo passou a ter `11` linhas por categoria
  (`automoveis`, `comerciais_leves` e `autos_comerciais_leves`) para o item
  `17` e para o item `18`; essa diferenca em relacao aos rankings por canal,
  que publicam `10` linhas, passa a ser tratada como comportamento esperado do
  bloco consolidado por marca
- com isso, a proxima frente prioritaria da fase 2 passa a ser o bloco de
  rankings por modelo separado por canal, iniciando pelos itens `19` e `20`
  nas paginas `30` e `31`

Atualizacao complementar de 2026-07-12 para os itens 19 e 20:

- os itens `19` e `20` foram concluidos no historico atualmente disponivel,
  reaproveitando o mesmo contrato estrutural do ranking geral por modelo em
  `market_vehicle_model_rankings`
- o parser das paginas `30` e `31` foi integrado a rotina mensal automatica da
  Fenabrave e ao preview operacional no Streamlit
- o piloto de `06/2026` foi executado com sucesso no banco real e liberou o
  backfill historico oficial dos itens `19` e `20`
- o backfill oficial dos itens `19` e `20` foi concluido para `12/2025` a
  `06/2026`, usando os `source_file_id` canonicos `17`, `5`, `4`, `3`, `2`,
  `6` e `13`
- todos os periodos carregados dos itens `19` e `20` ficaram com
  `status = validated` e `validation_status = passed` em
  `market_fenabrave_extraction_items`
- o item `20` manteve `row_count = 100` em todos os meses do historico
  atualmente disponivel
- o item `19` confirmou comportamento de `top N` variavel em
  `comerciais_leves`, com `row_count` entre `85` e `92` conforme o PDF
  publicado em cada mes
- no banco final, o item `19` manteve `50` linhas de `automoveis` em todos os
  meses e variou nas linhas de `comerciais_leves`, enquanto o item `20`
  manteve `50 + 50` no historico carregado
- com isso, a proxima frente prioritaria da fase 2 passa para os itens `21` e
  `22`, acumulados por canal nas paginas `32` e `33`

Atualizacao complementar de 2026-07-12 para o item 21:

- o item `21` foi concluido no historico atualmente disponivel, reaproveitando
  o mesmo contrato estrutural do item `19` em
  `market_vehicle_model_rankings`
- o parser da pagina `32` foi integrado a rotina mensal automatica da
  Fenabrave e ao preview operacional no Streamlit
- o piloto real de `06/2026` foi executado com sucesso no banco e liberou o
  backfill historico oficial do item `21`
- o backfill oficial do item `21` foi concluido para `12/2025` a `06/2026`,
  usando os `source_file_id` canonicos `17`, `5`, `4`, `3`, `2`, `6` e `13`
- todos os periodos carregados do item `21` passaram nos checks locais e foram
  gravados no mesmo fluxo operacional dos demais itens da fase `2`
- no banco final, o item `21` manteve `50` linhas de `automoveis` em todos os
  meses e confirmou `top N` variavel em `comerciais_leves`, com contagens
  entre `37` e `50` conforme o PDF publicado em cada periodo
- com isso, a proxima frente prioritaria da fase 2 passa a ser o item `22`,
  `Modelos mais emplacados venda varejo acumulado`, pagina `33`

Atualizacao complementar de 2026-07-12 para o item 22:

- o item `22` foi concluido no historico atualmente disponivel, reaproveitando
  o mesmo contrato estrutural do item `20` em
  `market_vehicle_model_rankings`
- o parser da pagina `33` foi integrado a rotina mensal automatica da
  Fenabrave e ao preview operacional no Streamlit
- o piloto real de `06/2026` foi executado com sucesso no banco e liberou o
  backfill historico oficial do item `22`
- o backfill oficial do item `22` foi concluido para `12/2025` a `06/2026`,
  usando os `source_file_id` canonicos `17`, `5`, `4`, `3`, `2`, `6` e `13`
- todos os periodos carregados do item `22` passaram nos checks locais e foram
  gravados no mesmo fluxo operacional dos demais itens da fase `2`
- no banco final, o item `22` manteve `50` linhas de `automoveis` e `50`
  linhas de `comerciais_leves` em todos os meses do historico atualmente
  disponivel
- com isso, o bloco `19` a `22` da fase `2` fica concluido no historico
  carregado e a proxima etapa passa a ser a revisao da fila prioritaria da
  Fenabrave apos o fechamento desse bloco

## Proximo passo apos aprovacao do plano

Depois da aprovacao deste plano, a execucao deve comecar pelo item 1:

```text
Ranking dos emplacamentos mes, pagina 6, automoveis e comerciais leves
```

O entregavel do item 1 deve incluir:

- DDL proposta
- parser especifico da pagina 6
- preview operacional
- validacoes do item
- carga de todos os PDFs existentes aplicaveis
- relatorio de cobertura historica
