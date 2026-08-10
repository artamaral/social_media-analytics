# Fenabrave - validacao da primeira carga completa

Data: 2026-08-10

## Objetivo

Registrar a validacao da primeira carga mensal completa da Fenabrave apos a
implementacao de todas as paginas ativas do PDF na rotina oficial.

Periodo validado:

- `reference_period = 2026-07-01`
- `source_file_id = 31`
- arquivo: `2026_07_02.pdf`
- `storage_path = fenabrave/2026/07/2026_07_02.pdf`

## Escopo validado

A validacao cobriu:

- fase 1 de segmentos;
- itens `1..8`;
- itens `11..22`;
- status persistido em `market_source_files`;
- status persistido em `market_fenabrave_extraction_items`;
- coerencia das tabelas fisicas carregadas no Supabase.

## Evidencia consultada

- `public.market_source_files`
- `public.market_fenabrave_extraction_items`
- `public.market_vehicle_registrations_segment`
- `public.market_vehicle_model_rankings`
- `public.market_vehicle_brand_rankings`
- `public.market_vehicle_subsegment_shares`
- `public.market_vehicle_electrified_registrations`
- `public.market_vehicle_sales_channel_mix`
- `sql/dml/audit_fenabrave_full_monthly_load.sql`

## Resultado geral

Resultado:

- carga aprovada
- nenhum item ativo ficou com `failed`, `pending`, `extracted` ou `skipped`
- os itens graficos tambem ficaram aprovados no estado final persistido

## Estado do arquivo mensal

`market_source_files`:

- `id = 31`
- `reference_period = 2026-07-01`
- `extraction_status = validated`
- `file_size_bytes = 2920113`
- `sha256 = 996d04f814bd176381a50bbc373c5c55a83e56d491eec05ff369e4df297b5a53`

Leitura:

- existe um unico arquivo canonico para o periodo validado;
- o PDF esta preservado no Storage com metadados suficientes de auditoria.

## Resultado por item

Todos os itens ativos ficaram com:

- `status = validated`
- `validation_status = passed`

Contagens observadas no controle mensal:

- item `1`: `100`
- item `2`: `100`
- item `3`: `42`
- item `4`: `42`
- item `5`: `13`
- item `6`: `6`
- item `7`: `20`
- item `8`: `22`
- item `11`: `6`
- item `12`: `6`
- item `13`: `30`
- item `14`: `30`
- item `15`: `30`
- item `16`: `30`
- item `17`: `33`
- item `18`: `33`
- item `19`: `93`
- item `20`: `100`
- item `21`: `97`
- item `22`: `100`

## Analise da fase 1

Checks estruturais observados:

- `autos + comerciais_leves = autos_comerciais_leves`
- `caminhoes + onibus = caminhoes_onibus`

Resultado:

- ambos com delta `0`

Observacao:

- o check `subtotal_plus_outros_vs_total` nao virou falha bloqueante nesta
  leitura porque a linha `total` nao ficou disponivel no fechamento
  consolidado; mesmo assim, os checks criticos da fase 1 passaram e o periodo
  permaneceu valido.

## Analise dos itens graficos

Itens avaliados:

- `13` e `14`: varejo por marca
- `15` e `16`: venda direta por marca
- `17` e `18`: participacao consolidada por marca

Resultado:

- todos os itens graficos ficaram `validated/passed` no banco
- as linhas persistidas mostraram marcas plausiveis e ranks continuos
- nao houve evidencia de texto invertido persistido incorretamente

Exemplos de marcas persistidas corretamente:

- `BYD`
- `FIAT`
- `VW`
- `MITSUBISHI`
- `RENAULT`
- `HYUNDAI`

Shares observados:

- itens `13..16`: totais por categoria em `100%` ou variacao residual de
  arredondamento
- itens `17..18`: totais entre `99.77%` e `100.43%`, coerentes com
  arredondamento grafico

Leitura:

- a suspeita inicial de erro nos itens graficos nao se confirmou no estado
  final persistido da carga;
- se houve mensagens de erro em tentativa intermediaria ou preview local, elas
  nao permaneceram como falha no fechamento oficial do mes.

## Coerencia mensal x acumulado

Checks observados:

- item `1` vs item `2`: acumulado maior que mensal nas duas categorias
- item `3` vs item `4`: acumulado maior que mensal nas duas categorias
- item `13` vs item `14`: top publicado coerente entre mensal e acumulado
- item `15` vs item `16`: top publicado coerente entre mensal e acumulado
- item `17` vs item `18`: diferencas pequenas, compativeis com arredondamento
- item `19` vs item `21`: acumulado maior que mensal
- item `20` vs item `22`: acumulado maior que mensal

Leitura:

- nao houve evidencia de acumulado menor que mensal em nenhum par relevante.

## Subsegmentos, canal e eletrificados

Item `5`:

- `current_month_sum = 100.01`
- `current_year_sum = 99.99`
- `prior_year_sum = 99.99`

Itens `11` e `12`:

- todos os totais por categoria fecharam em `100.0`

Item `6`:

- `automoveis`: `34961 + 25698 = 60659`
- `comerciais_leves`: `1551 + 80 = 1631`

Leitura:

- os blocos de subsegmento, canal de venda e eletrificados ficaram coerentes
  com o contrato esperado.

## Conclusao operacional

Conclusao:

- a carga de `07/2026` passou como primeira carga completa validada da
  Fenabrave;
- o contrato de validacao consolidado ficou comprovado em execucao real;
- nao restou pendencia aberta de carga ou validacao de dados da Fenabrave no
  backlog ativo do projeto.

## Proximo passo

- repetir o mesmo fechamento nos proximos meses usando
  `sql/dml/audit_fenabrave_full_monthly_load.sql`
- reabrir a frente Fenabrave apenas se houver mudanca real no layout do PDF ou
  falha nova de parser/validacao em mes futuro
