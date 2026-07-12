# Fenabrave fase 2 - Plano tecnico dos itens 13 a 18

Data: 2026-07-12

## Escopo

Este plano cobre os blocos graficos da Fenabrave ligados a participacao de
mercado por marca e ao breakdown por canal de venda.

Itens cobertos:

- `13` Ranking por marca de emplacamento varejo, pagina `26`, periodo `mes`
- `14` Ranking por marca de emplacamento varejo, pagina `27`, periodo
  `acumulado`
- `15` Ranking por marca de emplacamento venda direta, pagina `28`, periodo
  `mes`
- `16` Ranking por marca de emplacamento venda direta, pagina `29`, periodo
  `acumulado`
- `17` Participacao de mercado consolidada por marca, pagina `3`, periodo
  `mes`
- `18` Participacao de mercado consolidada por marca, pagina `4`, periodo
  `acumulado`

## Objetivo

Implementar extracao confiavel dos itens `13` a `18` com parser posicional,
preview no Streamlit, validacoes locais, persistencia no banco e backfill
historico dos PDFs ja preservados.

Todos esses itens devem, depois de aprovados, passar a fazer parte da inclusao
mensal automatica da Fenabrave.

## Conclusao tecnica da avaliacao de viabilidade

Resultado da avaliacao:

- a aquisicao dos dados das paginas `3`, `4`, `26`, `27`, `28` e `29` e
  viavel
- o erro do teste exploratorio antigo estava no metodo de extracao, nao na
  ausencia dos dados no PDF
- o layout se mostrou estavel entre `12/2025` e `06/2026`
- o parser correto para esse bloco deve ser `posicional por regiao`, sem OCR
  generico

## Evidencias observadas

Nas paginas `3`, `4`, `26`, `27`, `28` e `29`, os blocos publicados se
repetem com a mesma estrutura:

- `automoveis`
- `comerciais_leves`
- `autos_comerciais_leves`

Em cada bloco, a Fenabrave publica:

- uma lista ordenada de `marcas`
- um conjunto de `percentuais`
- distribuicao visual horizontal estavel por posicao `x`

O texto extraido do PDF pode vir invertido em varios casos, por exemplo:

- `DYB` em vez de `BYD`
- `TAIF` em vez de `FIAT`
- `WV` em vez de `VW`
- `IADNUYH` em vez de `HYUNDAI`
- `AOAC YREHC` em vez de `CAOA CHERY`

Mesmo assim, a posicao dos elementos permanece estavel o suficiente para montar
um parser confiavel.

## Contrato do parser

### Estrategia principal

Usar parser posicional por bloco, com as seguintes etapas:

1. abrir a pagina especifica
2. recortar os tres blocos por categoria
3. extrair palavras e percentuais dentro de cada bloco
4. separar candidatos a `marca` e candidatos a `share_pct`
5. corrigir texto invertido quando detectado
6. parear `marca` e `share_pct` por alinhamento horizontal
7. ordenar o resultado pelo eixo `x`, convertendo para `rank_position`
8. normalizar e validar antes de qualquer persistencia

### Blocos esperados por pagina

Todas as paginas `3`, `4`, `26`, `27`, `28` e `29` devem usar a mesma logica de
recorte por categoria:

- bloco 1: `automoveis`
- bloco 2: `comerciais_leves`
- bloco 3: `autos_comerciais_leves`

As coordenadas finais devem ser definidas na implementacao, mas o contrato do
parser deve assumir regioes fixas com tolerancia pequena e revisao visual no
preview do Streamlit.

### Regra obrigatoria de checagem de texto invertido

O parser deve aplicar verificacao explicita de texto invertido antes de aceitar
qualquer linha como valida.

Regra:

- toda `brand_name_raw` extraida deve passar por avaliacao de leitura normal e
  leitura invertida
- se a leitura invertida produzir marca mais plausivel que a leitura original,
  o parser deve persistir a versao corrigida
- a linha deve guardar evidencias suficientes para auditoria local, incluindo a
  forma bruta original quando necessario

Heuristicas minimas:

- detectar cadeias curtas conhecidas invertidas, como `WV`, `DYB`, `TAIF`
- detectar cadeias maiores claramente invertidas, como `IADNUYH`,
  `TLUANER`, `ATOYOT`
- permitir recomposicao de marcas compostas quando palavras adjacentes
  invertidas formarem marca valida, como `AOAC YREHC`
- registrar warning local quando houver ambiguidade entre texto normal e texto
  invertido

### Regra obrigatoria de pareamento por alinhamento

O parser nao deve depender apenas da ordem textual da pagina.

Regra:

- `marca` e `share_pct` devem ser associados pelo alinhamento em `x`
- a ordenacao final do ranking deve respeitar a sequencia visual do bloco
- se dois elementos competirem pelo mesmo slot horizontal, a linha deve entrar
  em warning ou falha, nunca em persistencia silenciosa

## Modelo de dados previsto

### Itens 13 a 16

Tabela-alvo prevista:

```text
market_vehicle_brand_rankings
```

Campos logicos principais:

- `source_file_id`
- `reference_period`
- `item_code`
- `published_period_type`
- `market_scope`
- `vehicle_category`
- `sales_channel`
- `rank_position`
- `brand_name_raw`
- `units = null`
- `market_share_pct`
- `raw_label`

Observacao:

- para os itens `13` a `16`, o valor publicado e percentual de participacao
  por marca; nao ha necessidade de `units` nesta etapa
- a modelagem adotada em 2026-07-12 passou a aceitar esse contrato na propria
  `market_vehicle_brand_rankings`, tornando `units` opcional para itens de
  share puro e preservando `market_share_pct` como medida principal

### Itens 17 e 18

Tabela-alvo prevista:

```text
market_vehicle_brand_market_share
```

Campos logicos principais:

- `source_file_id`
- `reference_period`
- `item_code`
- `published_period_type`
- `market_scope`
- `vehicle_category`
- `rank_position`
- `brand_name_raw`
- `share_pct`
- `raw_label`

## Validacoes minimas

### Validacoes estruturais

Aplicar a todos os itens `13` a `18`:

- a pagina deve conter exatamente `3` blocos esperados
- cada bloco deve produzir pelo menos `1` linha
- `rank_position` deve iniciar em `1`
- nao pode haver `rank_position` duplicado dentro do mesmo item e categoria
- `brand_name_raw` nao pode ficar vazia
- `share_pct` deve ficar entre `0` e `100`
- a ordem de `share_pct` deve ser decrescente ou empatar sem quebrar a ordem
  visual

### Validacoes especificas de texto invertido

- toda marca que entrar por reversao deve ser marcada como `reversed_text_fixed`
  no diagnostico local
- se a marca continuar pouco plausivel depois da reversao, o item deve gerar
  warning ou erro, nao seguir silenciosamente
- marcas compostas reconstruidas devem ser destacadas no preview local para
  auditoria

### Validacoes mensais versus acumuladas

Aplicar aos pares:

- item `13` contra item `14`
- item `15` contra item `16`
- item `17` contra item `18`

Checks:

- o acumulado deve manter as mesmas categorias do mensal
- o acumulado deve preservar apenas marcas plausiveis para o mesmo mercado
- percentuais nao devem ser recalculados a partir do mensal
- o acumulado deve ser tratado como dado publicado pelo PDF

### Validacoes entre consolidado e canal

Checks analiticos esperados:

- itens `17` e `18` funcionam como consolidado de mercado por marca
- itens `13` a `16` funcionam como breakdown por canal
- o conjunto de marcas dos itens `13` a `16` deve ser comparavel com o
  consolidado correspondente, aceitando diferenca de top N
- os percentuais publicados por canal nao devem ser somados automaticamente
  para tentar recompor o consolidado sem regra formal

## Regras do preview no Streamlit

O Streamlit deve exibir, para cada item:

- tabela preview das linhas extraidas
- checks estruturais
- diagnostico de texto invertido corrigido
- alerta quando houver linhas ambíguas

### Regra obrigatoria de mensagem de erro

Quando o parser identificar erro, a view do Streamlit deve mostrar mensagem
explícita e operacional.

Mensagem minima esperada:

```text
Falha na extracao do item Fenabrave. O parser identificou inconsistencias de
layout, alinhamento ou texto invertido e a persistencia foi bloqueada para este
item.
```

A mensagem deve ser complementada com pelo menos um detalhe:

- `item_code`
- `pagina`
- `vehicle_category` afetada, quando aplicavel
- tipo do erro detectado

Exemplos de tipo de erro:

- `brand_count_mismatch`
- `share_count_mismatch`
- `reversed_text_unresolved`
- `invalid_rank_order`
- `share_out_of_range`
- `ambiguous_x_alignment`

### Regra de bloqueio no Streamlit

- se um item tiver erro de parser, a persistencia desse item deve ser bloqueada
- o erro nao deve apagar itens anteriores ja validados
- o preview deve continuar visivel para revisao humana
- o status do item deve seguir como `failed` ou `warning`, conforme a gravidade

## Ordem de implementacao recomendada

1. fechar o parser dos itens `13` e `14`
2. fechar o parser dos itens `15` e `16`
3. fechar o parser dos itens `17` e `18`
4. integrar preview e mensagens de erro no Streamlit
5. integrar persistencia e controle em `market_fenabrave_extraction_items`
6. rodar piloto em `06/2026`
7. validar em `12/2025`
8. executar backfill historico dos meses disponiveis

## Status consolidado em 2026-07-12

- os itens `13` e `14` estao concluidos no historico atualmente disponivel
- o parser posicional ficou estabilizado para `12/2025` e `06/2026`, com
  diagnostico local de texto invertido e pareamento por alinhamento `x`
- o preview operacional no Streamlit passou a exibir as linhas extraidas, os
  checks estruturais e a mensagem explicita de bloqueio quando houver erro
- a persistencia mensal ficou ativa em `market_vehicle_brand_rankings`, usando
  `units = null` e `market_share_pct` como medida principal para rankings de
  share puro
- o parser passou a aceitar correcoes canonicas pontuais de marca apos a
  reversao do texto, como `ITSUBISHI -> MITSUBISHI`, mantendo o bruto para
  auditoria local
- o backfill historico oficial dos itens `13` e `14` foi concluido para os
  `source_file_id` `17`, `5`, `4`, `3`, `2`, `6` e `13`, cobrindo `12/2025`
  a `06/2026`
- a atividade corrente a partir deste ponto passa a ser o item `15`, pagina
  `28`, `Ranking por marca de emplacamento venda direta` no periodo `mes`,
  reaproveitando o mesmo contrato posicional dos itens `13` e `14`

## Criterio de aceite

Os itens `13` a `18` so devem ser promovidos para a rotina mensal automatica
quando:

- o parser posicional estiver estavel em `06/2026` e `12/2025`
- a regra de texto invertido estiver ativa e auditavel
- o Streamlit mostrar mensagem clara de erro quando houver falha
- a persistencia estiver bloqueada em caso de erro real
- o backfill historico do intervalo disponivel estiver validado
