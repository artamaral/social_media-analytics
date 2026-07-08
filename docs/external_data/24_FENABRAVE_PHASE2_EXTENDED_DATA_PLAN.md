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
| 5 | Modelos mais emplacados automoveis por subsegmento | 17 | acumulado | automoveis | sim |
| 6 | Mercado de eletrificados autos | 20 | mes | eletricos e hibridos | sim |
| 7 | Total por marca leves hibrido | 20 | mes | leves hibridos | sim |
| 8 | Total por marca leves eletrico | 20 | mes | leves eletricos | sim |
| 9 | Total por modelo leves hibrido | 20 | mes | leves hibridos | sim |
| 10 | Total por modelo leves eletrico | 20 | mes | leves eletricos | sim |
| 11 | Participacao de venda direta e varejo | 24 | mes | canal de venda | sim |
| 12 | Participacao de venda direta e varejo | 25 | acumulado | canal de venda | sim |
| 13 | Ranking por marca de emplacamento varejo | 26 | mes | varejo | sim |
| 14 | Ranking por marca de emplacamento varejo | 27 | acumulado | varejo | sim |
| 15 | Ranking por marca de emplacamento direta | 28 | mes | venda direta | sim |
| 16 | Ranking por marca de emplacamento direta | 29 | acumulado | venda direta | sim |
| 17 | Modelos mais emplacados venda direta | 30 | mes | venda direta | sim |
| 18 | Modelos mais emplacados venda varejo | 31 | mes | varejo | sim |
| 19 | Modelos mais emplacados venda direta | 32 | acumulado | venda direta | sim |
| 20 | Modelos mais emplacados venda varejo | 33 | acumulado | varejo | sim |

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
| 2.5 | 17 a 20 | rankings por modelo separados por canal |
| 2.6 | 6 a 10 | eletrificados, com taxonomia propria de combustivel/propulsao |
| 2.7 | 5 | modelos por subsegmento, que exige maior cuidado de taxonomia |

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
units
market_share_pct
raw_label
created_at
```

Chave unica sugerida:

```text
source_file_id, item_code, published_period_type, sales_channel, rank_position, brand_name
```

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
- 9
- 10

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
vehicle_category             -- leves
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

### 6. Participacao por canal de venda

Itens cobertos:

- 11
- 12

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
units
share_pct
raw_label
created_at
```

Chave unica sugerida:

```text
source_file_id, item_code, published_period_type, sales_channel, vehicle_category
```

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
9. Repetir ate o item 20
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

Aplicar aos itens 1, 2, 3, 4, 13, 14, 15, 16, 17, 18, 19 e 20:

- ranking deve iniciar em 1
- ranking nao deve ter posicoes duplicadas dentro do item
- unidades devem ser decrescentes ou empatar sem quebrar a ordem visual
- top N extraido deve bater com a quantidade de linhas esperada da pagina
- total das linhas do ranking nao deve exceder o total do segmento/canal
  correspondente quando houver base comparavel

### Validacoes de mensal versus acumulado

Aplicar aos pares:

- item 1 contra item 2
- item 3 contra item 4
- item 11 contra item 12
- item 13 contra item 14
- item 15 contra item 16
- item 17 contra item 19
- item 18 contra item 20

Checks:

- acumulado do ano deve ser maior ou igual ao valor mensal do mesmo periodo
- acumulado de um mes deve ser maior ou igual ao acumulado do mes anterior
  dentro do mesmo ano, quando o item existir nos dois meses
- em janeiro, acumulado deve ser igual ou muito proximo do mensal, salvo regra
  especifica do PDF
- acumulado publicado deve ser tratado como dado publicado, nao recalculado
  silenciosamente pela soma mensal sem comparacao

### Validacoes de canal de venda

Aplicar aos itens 11 a 20:

- `retail + direct` deve bater com o total comparavel quando o PDF trouxer a
  base
- participacoes de varejo e direta devem somar 100% ou fechar dentro da margem
  de arredondamento definida
- rankings de varejo e direta devem ter `sales_channel` preenchido corretamente
- itens mensais e acumulados nao devem ser misturados

### Validacoes de eletrificados

Aplicar aos itens 6 a 10:

- `powertrain_type` deve ser sempre `electric` ou `hybrid`
- itens de marca nao devem gravar `model_name`
- itens de modelo devem gravar `brand_name` e `model_name`, quando o PDF
  permitir identificar ambos
- totais por marca/modelo nao devem exceder o total de eletrificados do mesmo
  tipo de propulsao, salvo se o PDF usar recorte diferente documentado
- eletricos e hibridos devem ser carregados como categorias separadas

### Validacoes de subsegmento

Aplicar ao item 5:

- `subsegment_name` obrigatorio
- cada subsegmento deve ter ranking independente
- posicoes podem reiniciar por subsegmento
- modelo nao deve aparecer em subsegmentos conflitantes no mesmo periodo sem
  registro de excecao

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

Pendencias para a fase 2 a partir deste ponto:

- iniciar o item 2 com o mesmo padrao de parser, preview, validacao e backfill
- iniciar o item 3 em seguida, mantendo a implantacao incremental por item
- manter a documentacao e a auditoria de cobertura atualizadas a cada novo item
  liberado

### Item 2 em andamento

Atualizacao de 2026-07-08:

- o `Ranking dos emplacamentos acumulado` foi confirmado na pagina `7` do PDF,
  e nao na pagina `6`
- o parser do item 2 passou a reutilizar o mesmo contrato estrutural do item 1
  em `market_vehicle_model_rankings`
- o preview operacional passou a exibir o item 2 junto do item 1 no Streamlit
- o `dry-run` de junho/2026 validou a extracao estrutural do item 2 com `50`
  linhas por categoria e checks locais aprovados
- ainda falta concluir a gravacao historica dos meses ja disponiveis e registrar
  o status final do item 2 em todos os periodos

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
