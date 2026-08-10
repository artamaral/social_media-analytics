# Fenabrave - checklist de validacao da carga completa

Data: 2026-08-10

## Objetivo

Definir o processo oficial de validacao para o primeiro carregamento completo
da Fenabrave depois da implementacao de todas as paginas ativas do PDF.

Este documento fecha a lacuna entre:

- o parser mensal da rotina Fenabrave;
- as validacoes locais do script;
- os testes SQL por item ja existentes;
- a aprovacao final do mes como carga confiavel.

## Quando usar

Usar este checklist sempre que um novo PDF mensal da Fenabrave for processado
com a cobertura ativa completa:

- fase 1 de segmentos;
- itens `1..8`;
- itens `11..22`.

Para este primeiro carregamento completo, tratar o processo como validacao de
homologacao operacional, nao apenas como rotina mensal comum.

## Artefatos oficiais

- script de ingestao: `scripts/fenabrave_ingestion/ingest_fenabrave_phase1.py`
- runbook operacional: `scripts/fenabrave_ingestion/README.md`
- calendario offline: `docs/external_data/00_OFFLINE_OPERATIONS_CALENDAR.md`
- checks de data quality: `docs/data_model/03_DATA_QUALITY_CHECKS.md`
- auditoria consolidada: `sql/dml/audit_fenabrave_full_monthly_load.sql`

## Regra de aprovacao

A carga do mes so pode ser tratada como aprovada quando todos os blocos abaixo
forem verdadeiros:

1. existe um unico `market_source_files` canonico para o `reference_period`;
2. o PDF do mes esta preservado no Storage com `storage_bucket`, `storage_path`,
   `file_size_bytes` e `sha256`;
3. a fase 1 de segmentos passou nos checks estruturais;
4. todos os itens ativos `1..8` e `11..22` existem em
   `market_fenabrave_extraction_items`;
5. todos esses itens estao com `status in ('validated', 'warning_accepted')`;
6. nenhum item ativo do mes ficou como `pending`, `extracted`, `failed` ou
   `skipped`;
7. o `row_count` do controle bate com a contagem real nas tabelas fisicas;
8. os checks de coerencia mensal x acumulado passaram;
9. warnings remanescentes foram revisados e registrados como aceitos por causa
   conhecida de layout/arredondamento, nunca por falta de cobertura.

## Tipos de resultado

### `passed`

Sem acao adicional. O check pode ser tratado como confiavel.

### `warning`

Pode ser aceito apenas se:

- houver explicacao objetiva;
- o dado continuar utilizavel;
- a justificativa ficar registrada em `validation_notes` ou no fechamento da carga.

Exemplos aceitaveis:

- diferenca marginal de arredondamento em shares;
- ausencia do total geral da fase 1 quando os checks criticos de soma ainda
  passam e a revisao visual do PDF confirma o valor publicado.

### `failed`

Bloqueia aprovacao do mes. A carga nao deve ser considerada fechada ate que o
problema seja corrigido ou reprocessado.

## Fluxo operacional recomendado

### 1. Pre-flight do arquivo

Confirmar:

- URL oficial do PDF;
- upload no bucket `market-source-files`;
- `reference_period` correto;
- inexistencia de duplicidade canonica em `market_source_files`.

### 2. Dry-run do parser

Rodar o script em `--dry-run` e revisar:

- preview da fase 1;
- preview dos itens da fase 2;
- validacoes locais impressas no terminal;
- qualquer quebra visual nova do layout.

Se o dry-run mostrar falha estrutural, nao seguir para `--write`.

### 3. Gravacao controlada

Rodar em `--write` somente depois do preview estar coerente.

Durante a gravacao:

- revisar o PDF aberto;
- confirmar o mes visualmente;
- nao aceitar `OK` se houver pagina faltando, ranks quebrados ou contagens vazias.

### 4. Auditoria SQL consolidada

Executar `sql/dml/audit_fenabrave_full_monthly_load.sql`, ajustando apenas o
`target_period` no topo do arquivo.

O SQL fecha a carga em 8 blocos:

1. unicidade do arquivo canonico;
2. metadados minimos do PDF;
3. cobertura e status dos itens ativos;
4. consistencia entre `row_count` do controle e linhas reais;
5. integridade dos segmentos da fase 1;
6. coerencia mensal x acumulado entre pares de itens;
7. soma de shares dos itens de canal e subsegmento;
8. coerencia do item 6 entre hibridos, eletricos e total eletrificado.

### 5. Fechamento manual do mes

Registrar o mes como concluido apenas se:

- nao houver `failed`;
- warnings estiverem entendidos e aceitos;
- a leitura final bater com o PDF e com as tabelas carregadas.

## Matriz de severidade

Bloqueadores imediatos:

- mais de um `source_file_id` para o periodo;
- item ativo ausente no controle;
- item ativo com `pending`, `extracted`, `failed` ou `skipped`;
- `row_count` do controle diferente do dado real;
- fase 1 quebrada em `autos + comerciais_leves` ou `caminhoes + onibus`;
- acumulado menor que o mensal no mesmo recorte;
- share de canal fora da tolerancia esperada;
- item 6 com total eletrificado diferente de `hibridos + eletricos`.

Warnings revisaveis:

- total de share ligeiramente diferente de `100` por arredondamento;
- quantidade publicada de ranks variando por mudanca de layout, desde que os
  ranks estejam continuos e o item permaneca integro;
- `subtotal_plus_outros_vs_total` sem total geral identificavel, desde que a
  revisao visual confirme o PDF e os checks criticos tenham passado.

## Evidencia minima para considerar o mes validado

Guardar ou registrar:

- comando usado no `--write`;
- `reference_period` validado;
- `source_file_id` canonico;
- resultado da auditoria consolidada;
- lista de warnings aceitos, se houver.

## Proximo passo recomendado

Depois deste primeiro carregamento completo, o mesmo checklist passa a ser o
contrato padrao da rotina mensal da Fenabrave.
